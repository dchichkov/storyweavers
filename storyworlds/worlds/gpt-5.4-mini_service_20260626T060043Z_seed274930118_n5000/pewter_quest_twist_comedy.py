#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny comedy quest about pewter, with a
light twist and a happy ending.

The source tale imagines a small, funny quest:
A child wants to deliver a shiny pewter cup to the town's tiny bell-ringer.
Along the way, a mix-up makes the cup seem lost, but the "mystery" turns out to
be silly: the cup was hiding under a floppy hat the whole time. The child and a
friend solve the little puzzle, laugh, and finish the quest together.

This file implements that premise as a small simulation with physical meters and
emotional memes, plus an inline ASP twin for the reasonableness gate.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_under: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def emo(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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
        return World(
            place=self.place,
            entities=dataclasses.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dataclasses.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    item: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class PlaceDef:
    place: str
    quest_site: str
    clutter: str


@dataclass(frozen=True)
class ItemDef:
    label: str
    phrase: str
    shine: str
    awkward: str
    value: str


PLACES = {
    "workshop": PlaceDef(place="the workshop", quest_site="the workbench", clutter="a pile of feathers"),
    "market": PlaceDef(place="the market", quest_site="the fountain", clutter="a stack of paper hats"),
    "garden": PlaceDef(place="the garden", quest_site="the garden gate", clutter="a basket of windy ribbons"),
}

ITEMS = {
    "cup": ItemDef(label="cup", phrase="a small pewter cup", shine="shiny", awkward="clinky", value="badge"),
    "spoon": ItemDef(label="spoon", phrase="a pewter spoon with a round handle", shine="dull-bright", awkward="tippy", value="token"),
    "locket": ItemDef(label="locket", phrase="a pewter locket", shine="softly shiny", awkward="fiddly", value="treasure"),
}

HEROES = ["Pip", "Mina", "Joss", "Tara", "Nell", "Bram"]
FRIENDS = ["Midge", "Polo", "Wren", "Zuzu", "Ollie", "Bibi"]


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def setting_line(world: World) -> str:
    return {
        "the workshop": "The workshop smelled like wood shavings and warm tea.",
        "the market": "The market buzzed with carts, bells, and a lot of very serious apples.",
        "the garden": "The garden looked busy with vines, stones, and one extremely proud snail.",
    }[world.place]


def intro(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(f"{hero.id} was a cheerful little helper who loved a good quest and a good laugh.")
    world.say(f"{hero.pronoun().capitalize()} had promised to carry {hero.pronoun('possessive')} {item.phrase} to the town's little bell-ringer.")
    world.say(f"{friend.id} came along because every quest is better with one brave friend and one bad joke.")


def start_quest(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["purpose"] = hero.memes.get("purpose", 0) + 1
    item.carried_by = hero.id
    item.meters["safe"] = item.meters.get("safe", 0) + 1
    world.say(setting_line(world))
    world.say(f"They set out toward {world.facts['quest_site']} with {item.phrase} tucked carefully in {hero.pronoun('possessive')} hands.")


def twist_mixup(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["silly"] = friend.memes.get("silly", 0) + 1
    world.say(
        f"At the busiest corner, {friend.id} tossed up a floppy hat for a joke, and the hat landed right over {item.phrase}."
    )
    item.hidden_under = "hat"
    item.meters["hidden"] = item.meters.get("hidden", 0) + 1
    item.carried_by = None
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    world.say(f"{hero.id} blinked. 'My {item.label} is gone!' {hero.pronoun()} cried, even though it was only hiding.")

    if "search_alarm" not in world.fired:
        world.fired.add("search_alarm")
        hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1
        friend.memes["guilt"] = friend.memes.get("guilt", 0) + 1


def solve_twist(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.meters["looking"] = hero.meters.get("looking", 0) + 1
    friend.meters["peek"] = friend.meters.get("peek", 0) + 1
    world.say(f"They searched under crates, behind baskets, and even inside a tub of turnips.")
    world.say(f"Then {friend.id} sneezed at the hat, the hat wobbled, and {item.phrase} flashed in the light.")
    item.hidden_under = None
    item.carried_by = hero.id
    item.meters["safe"] = item.meters.get("safe", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    world.say(f"{hero.id} laughed so hard {hero.pronoun()} nearly bowed to the hat.")
    world.say(f"'Good mystery,' {hero.id} said. 'Very sneaky cup. Very sneaky hat.'")


def end_quest(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"Together they finished the quest at {world.facts['quest_site']}, where the bell-ringer accepted the {item.label} with a smile."
    )
    world.say(
        f"In the end, {hero.id} carried the {item.label} home, {friend.id} wore the hat like a champion, and the whole lane stayed bright with laughter."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    item: ItemDef = world.facts["item_def"]  # type: ignore[assignment]
    return [
        f'Write a short funny story for a young child about a {item.label} and a silly quest.',
        f"Tell a light comedy about a child who must deliver {item.phrase} but gets caught in a small mix-up.",
        f"Write a story with a quest, a twist, and a happy ending that includes the word 'pewter'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    item_def: ItemDef = world.facts["item_def"]  # type: ignore[assignment]
    place: PlaceDef = world.facts["place_def"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What was {hero.id} trying to deliver on the quest?",
            answer=f"{hero.id} was trying to deliver {hero.pronoun('possessive')} {item_def.phrase} to the town's bell-ringer.",
        ),
        QAItem(
            question=f"What silly thing caused the twist in the story?",
            answer=f"A floppy hat landed over the {item.label} and made everyone think it had disappeared.",
        ),
        QAItem(
            question=f"Where did the quest lead them?",
            answer=f"The quest led them to {place.quest_site} in {place.place}, where the bell-ringer was waiting.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The joke was solved, {hero.id} got the {item.label} back, and everyone finished the quest laughing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pewter?",
            answer="Pewter is a soft metal that can be shaped into cups, spoons, medals, and little shiny objects.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or task where someone goes looking for something important or tries to finish a goal.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes what people thought was happening.",
        ),
        QAItem(
            question="Why can a floppy hat be funny in a story?",
            answer="A floppy hat can be funny because it can hide things, wobble around, or make a serious moment look silly.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is reasonable when the place supports it, the item is made of pewter,
% and the story includes a comedic twist caused by a covering object.
pewter_item(I) :- item(I).
quest_ok(P, I) :- place(P), item(I), pewter_item(I), twist_cover(I), site(P,_).
twist_cover(I) :- hidden_under(I, hat).
valid_story(P, I) :- quest_ok(P, I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("site", pid, place.quest_site))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("pewter_item", iid))
    lines.append(asp.fact("hidden_under", "cup", "hat"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("workshop", "cup"), ("market", "cup"), ("garden", "cup")}
    clingo_set = set(asp_valid())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches Python reasonableness ({len(clingo_set)} cases).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP only:", sorted(clingo_set - python_set))
    print("Python only:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for item in ITEMS:
            combos.append((place, item, "hat"))
    return combos


def explain_rejection(place: str, item: str) -> str:
    return f"(No story: the quest setup for {item} at {place} does not create a proper comic twist.)"


# ---------------------------------------------------------------------------
# Story synthesis
# ---------------------------------------------------------------------------
def tell(place: PlaceDef, hero_name: str, friend_name: str, item_def: ItemDef) -> World:
    world = World(place=place.place)
    world.facts["quest_site"] = place.quest_site
    world.facts["item_def"] = item_def
    world.facts["place_def"] = place

    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type="child"))
    item = world.add(
        Entity(
            id=item_def.label,
            kind="thing",
            label=item_def.label,
            phrase=item_def.phrase,
            type="thing",
            owner=hero.id,
        )
    )
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["item"] = item

    intro(world, hero, friend, item)
    world.para()
    start_quest(world, hero, item)
    world.para()
    twist_mixup(world, hero, friend, item)
    solve_twist(world, hero, friend, item)
    world.para()
    end_quest(world, hero, friend, item)
    return world


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy quest world about pewter, a twist, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    item = args.item or rng.choice(list(ITEMS))
    if (place, item, "hat") not in valid_combos():
        raise StoryError(explain_rejection(place, item))
    hero = args.name or rng.choice(HEROES)
    friend = args.friend or rng.choice(FRIENDS)
    if friend == hero:
        friend = next(x for x in FRIENDS if x != hero)
    return StoryParams(place=place, hero=hero, friend=friend, item=item)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero, params.friend, ITEMS[params.item])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_under:
            bits.append(f"hidden_under={e.hidden_under}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {', '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid stories:")
        for p, i in asp_valid():
            print(f"  {p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="workshop", hero="Pip", friend="Midge", item="cup"),
            StoryParams(place="market", hero="Mina", friend="Bibi", item="spoon"),
            StoryParams(place="garden", hero="Joss", friend="Wren", item="locket"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend} | {p.place} | {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
