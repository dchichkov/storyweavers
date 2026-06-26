#!/usr/bin/env python3
"""
A small slice-of-life storyworld set in an airport.

Seed premise:
- A furry cartoon child is traveling through an airport.
- A small everyday temptation or mistake leads to a moral choice.
- The ending should feel warm, concrete, and grounded in a visible change.

This world uses a simple world model with physical meters and emotional memes,
plus a lightweight ASP twin for parity checks.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner_kind: str = "child"
    value: str = "small"
    moral_weight: str = "honest"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    item: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lila", "Zoe", "Nora", "Ava", "June"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Leo", "Ezra"]

ITEMS = {
    "toy_plane": Item(
        id="toy_plane",
        label="toy plane",
        phrase="a tiny blue toy plane",
        value="small",
        moral_weight="honest",
    ),
    "scarf": Item(
        id="scarf",
        label="scarf",
        phrase="a soft red scarf",
        value="small",
        moral_weight="kind",
    ),
    "sketchbook": Item(
        id="sketchbook",
        label="sketchbook",
        phrase="a little sketchbook with a cardboard cover",
        value="small",
        moral_weight="careful",
    ),
}

MORAL_VALUE = {
    "honest": "It is better to tell the truth than to hide a mistake.",
    "kind": "Kindness means helping someone even when no one is watching.",
    "careful": "Careful hands keep small things safe.",
}

PARKING_LOT = "the airport"
FOOTER_TEXT = "footer note"
FOOTER_WORD = "footer"
FURRY_WORD = "furry"
CARTOON_WORD = "cartoon"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(place=PARKING_LOT)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a furry cartoon {params.gender}",
        meters={"tired": 0.0, "careful": 0.0, "warmth": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "pride": 0.0, "guilt": 0.0, "kindness": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        phrase=f"the {params.parent}",
        meters={"busy": 0.0, "patience": 0.0},
        memes={"trust": 0.0},
    ))
    item = ITEMS[params.item]
    lost = world.add(Entity(
        id="lost_item",
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner="unknown",
        caretaker=params.name,
        meters={"lost": 1.0, "clean": 1.0},
        memes={"value": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, item=lost, item_spec=item)
    return world


def tell_story(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    item_spec: Item = f["item_spec"]

    world.say(
        f"{hero.label} was a {FURRY_WORD} {CARTOON_WORD} kid at {world.place}, "
        f"walking beside {parent.label} with a small suitcase that bumped softly on the floor."
    )
    world.say(
        f"At the bottom of a bright airport map, a tiny {FOOTER_WORD} {FOOTER_TEXT} "
        f"said where the restrooms and gates were."
    )
    world.say(
        f"Near a seat by the charging wall, {hero.label} found {item.phrase}. "
        f"{hero.label} liked how neat it looked and slipped it into {hero.pronoun('possessive')} pocket."
    )

    hero.memes["worry"] += 1
    hero.memes["guilt"] += 1
    world.para()
    world.say(
        f"Then {hero.label} noticed a child at the nearby gate looking around with a wet face and empty hands. "
        f"The child had been asking about {item.label}."
    )
    world.say(
        f"{parent.label} saw the pocket bulge and asked, "
        f"\"Did you find something that belongs to someone else?\""
    )

    if item_spec.moral_weight == "honest":
        world.say(
            f"{hero.label} looked down, nodded, and held the {item.label} out with both hands. "
            f"\"I found it, and I should give it back,\" {hero.pronoun()} said."
        )
    elif item_spec.moral_weight == "kind":
        world.say(
            f"{hero.label} took a breath, walked over, and offered the {item.label} back before anyone had to ask. "
            f"\"I think this is yours,\" {hero.pronoun()} said."
        )
    else:
        world.say(
            f"{hero.label} remembered that careful hands keep small things safe, so {hero.pronoun()} carried the {item.label} back to the seat where it had fallen."
        )

    hero.memes["worry"] -= 0.5
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.memes["kindness"] += 1
    parent.memes["trust"] += 1

    world.para()
    world.say(
        f"The other child smiled wide and hugged the {item.label} close. "
        f"{parent.label} rubbed {hero.pronoun('possessive')} shoulder and smiled too."
    )
    world.say(
        f"By the time the boarding call echoed over the loudspeakers, {hero.label} felt lighter. "
        f"The little mistake had turned into a good choice, and the airport felt warmer than before."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    item: Entity = world.facts["item"]
    return [
        f"Write a short slice-of-life story about a {FURRY_WORD} {CARTOON_WORD} child at an airport who learns a moral value.",
        f"Tell a gentle airport story where {hero.label} finds {item.phrase} and makes an honest choice.",
        f"Write a child-friendly story with a {FOOTER_WORD} note in the airport map and a warm ending about doing the right thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    parent: Entity = world.facts["parent"]
    item: Entity = world.facts["item"]
    return [
        QAItem(
            question=f"What kind of child is {hero.label}?",
            answer=f"{hero.label} is a furry cartoon child at the airport, walking beside {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.label} find near the seats?",
            answer=f"{hero.label} found {item.phrase} near a seat by the charging wall.",
        ),
        QAItem(
            question=f"What did {hero.label} do after noticing the other child looking for the {item.label}?",
            answer=f"{hero.label} told the truth and gave the {item.label} back with both hands.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the lost item returned, the parent smiling, and the airport feeling warmer and calmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a footer note?",
            answer="A footer note is a small line of text printed at the bottom of a page or sign.",
        ),
        QAItem(
            question="What is an airport?",
            answer="An airport is a place where people go to catch planes and travel to other places.",
        ),
        QAItem(
            question="What does moral value mean?",
            answer="A moral value is an important lesson about how to treat other people, like honesty or kindness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(airport).
moral_value(honesty).
moral_value(kindness).
moral_value(carefulness).

word(footer).
word(furry).
word(cartoon).

valid_story(P, M) :- place(P), moral_value(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("place", "airport"),
        asp.fact("word", "footer"),
        asp.fact("word", "furry"),
        asp.fact("word", "cartoon"),
        asp.fact("moral_value", "honesty"),
        asp.fact("moral_value", "kindness"),
        asp.fact("moral_value", "carefulness"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("airport", "honesty"), ("airport", "kindness"), ("airport", "carefulness")}
    if atoms == expected:
        print(f"OK: ASP parity check passed ({len(atoms)} valid story values).")
        return 0
    print("MISMATCH between ASP and Python expectations:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life airport storyworld.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--item", choices=sorted(ITEMS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    item = args.item or rng.choice(sorted(ITEMS))
    return StoryParams(name=name, gender=gender, parent=parent, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print()
        print("--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(eid, ent.kind, ent.type, ent.meters, ent.memes)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", item="toy_plane"),
    StoryParams(name="Leo", gender="boy", parent="father", item="scarf"),
    StoryParams(name="Nora", gender="girl", parent="mother", item="sketchbook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        for a in atoms:
            print(a)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
