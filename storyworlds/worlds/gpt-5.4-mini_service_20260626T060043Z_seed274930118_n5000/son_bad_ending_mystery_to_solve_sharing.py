#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/son_bad_ending_mystery_to_solve_sharing.py
======================================================================================================================

A small slice-of-life storyworld about a son, a missing thing, and a sharing
problem that turns into a little mystery. The stories are deliberately modest:
a child notices something missing, follows a few plain clues, and learns a
truth that changes the mood of the day.

The domain supports:
- a son character
- a shared item or shared food
- a mystery to solve
- a bad ending / bittersweet ending option
- child-facing prose with a concrete, state-driven turn
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World constants
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
    carried_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    affordances: set[str] = field(default_factory=set)


@dataclass
class ShareThing:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    can_be_shared: bool = True
    can_be_lost: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_label: str
    clue_label: str
    revealed_by: str
    bad_ending: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place("the kitchen", indoors=True, affordances={"sharing", "finding"}),
    "living_room": Place("the living room", indoors=True, affordances={"sharing", "finding"}),
    "yard": Place("the yard", indoors=False, affordances={"sharing", "finding"}),
    "porch": Place("the porch", indoors=False, affordances={"sharing", "finding"}),
}

SHARE_THINGS = {
    "cookies": ShareThing(
        id="cookies",
        label="cookies",
        phrase="three warm cookies on a plate",
        type="cookies",
        plural=True,
        can_be_shared=True,
        can_be_lost=False,
        tags={"share", "food"},
    ),
    "crayons": ShareThing(
        id="crayons",
        label="crayons",
        phrase="a box of bright crayons",
        type="crayons",
        plural=True,
        can_be_shared=True,
        can_be_lost=True,
        tags={"share", "color"},
    ),
    "marble": ShareThing(
        id="marble",
        label="marble",
        phrase="one glass marble with a blue swirl",
        type="marble",
        plural=False,
        can_be_shared=False,
        can_be_lost=True,
        tags={"mystery", "toy"},
    ),
    "stickers": ShareThing(
        id="stickers",
        label="stickers",
        phrase="a sheet of animal stickers",
        type="stickers",
        plural=True,
        can_be_shared=True,
        can_be_lost=True,
        tags={"share", "toy"},
    ),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        id="missing_cookie",
        missing_label="cookie",
        clue_label="crumbs",
        revealed_by="a little crumb trail on the table",
        bad_ending=True,
    ),
    "missing_marble": Mystery(
        id="missing_marble",
        missing_label="marble",
        clue_label="a blue shine under the couch",
        revealed_by="a blue glint under the couch",
        bad_ending=True,
    ),
    "missing_crayons": Mystery(
        id="missing_crayons",
        missing_label="crayon",
        clue_label="smudges",
        revealed_by="red and green smudges on the paper",
        bad_ending=False,
    ),
}

BOY_NAMES = ["Noah", "Eli", "Theo", "Milo", "Jude", "Finn", "Ben", "Leo"]
GIRL_NAMES = ["Maya", "Nora", "Lily", "Ada", "Zoe", "Mia"]

TRAITS = ["quiet", "careful", "gentle", "curious", "patient"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    mystery: str
    name: str = "Noah"
    gender: str = "boy"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / constraints
# ---------------------------------------------------------------------------
def valid_combo(place: str, item: str, mystery: str) -> bool:
    thing = SHARE_THINGS[item]
    mys = MYSTERIES[mystery]
    if item == "marble" and mystery != "missing_marble":
        return False
    if item == "cookies" and mystery != "missing_cookie":
        return False
    if item == "crayons" and mystery != "missing_crayons":
        return False
    return place in PLACES and thing.can_be_shared and thing.tags.intersection({"share", "mystery", "food", "toy", "color"})


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for item in SHARE_THINGS:
            for m in MYSTERIES:
                if valid_combo(p, item, m):
                    combos.append((p, item, m))
    return combos


def explain_rejection(item: str, mystery: str) -> str:
    return f"(No story: {item} does not fit the mystery '{mystery}' in a way that can be solved naturally.)"


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------
def _share_action(world: World, son: Entity, item: Entity, other: Entity) -> None:
    item.meters["shared"] = item.meters.get("shared", 0.0) + 1
    item.shared_with.add(other.id)
    son.memes["generous"] = son.memes.get("generous", 0.0) + 1
    other.memes["happy"] = other.memes.get("happy", 0.0) + 1
    world.say(f"{son.id} split the {item.label} with {other.id}, and for a moment the room felt softer.")


def _lose_item(world: World, item: Entity) -> None:
    item.meters["missing"] = 1.0


def _reveal_clue(world: World, clue_text: str) -> None:
    world.say(clue_text)


def solve_mystery(world: World, son: Entity, item: Entity, mystery: Mystery, parent: Entity, sibling: Entity) -> None:
    world.say(f"Then {son.id} noticed {mystery.revealed_by}.")
    if mystery.id == "missing_cookie":
        world.say(f"{son.id} followed the crumbs to {sibling.id}'s hands. {sibling.id} looked down at the empty plate and said sorry.")
        world.say(f"{parent.id} sighed and said the cookies were gone now, so there would not be one left for later.")
        son.memes["sad"] = 1.0
        son.memes["understands"] = 1.0
    elif mystery.id == "missing_marble":
        world.say(f"The blue glint was {item.label}. It had rolled under the couch and stayed there, out of reach.")
        world.say(f"{son.id} pulled it out, but the game was already over, and the afternoon felt smaller than before.")
        son.memes["relief"] = 1.0
        son.memes["sad"] = 1.0
    else:
        world.say(f"The smudges showed that {sibling.id} had used the crayons too, and the picture on the page was almost finished.")
        world.say(f"{son.id} saw that the crayons were still shared, even if the tidy box was not tidy anymore.")
        son.memes["understands"] = 1.0


def tell_story(place: Place, item_cfg: ShareThing, mystery_cfg: Mystery, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    son = world.add(Entity(id=name, kind="character", type=gender, label="son", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    sibling = world.add(Entity(id="Rae", kind="character", type="girl", label="little sister"))
    item = world.add(Entity(id=item_cfg.id, kind="thing", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, plural=item_cfg.plural, owner=son.id))
    mystery = mystery_cfg

    # Act 1
    world.say(f"{son.id} was a {trait} son who liked to keep track of little things.")
    world.say(f"At {place.name}, {son.id} saw {item.phrase}.")
    world.say(f"{son.id} wanted to share {item.item_pronoun()} with {sibling.id}, and that made the afternoon feel kind.")
    world.para()

    # Act 2
    world.say(f"Later, something was gone.")
    if item_cfg.id == "cookies":
        _lose_item(world, item)
        world.say(f"The plate that had held the cookies was suddenly empty.")
    elif item_cfg.id == "marble":
        _lose_item(world, item)
        world.say(f"The blue marble was nowhere on the floor where {son.id} had left it.")
    elif item_cfg.id == "crayons":
        world.say(f"The box of crayons was open, but the green crayon was missing from its slot.")
        _lose_item(world, item)
    else:
        _lose_item(world, item)
    world.say(f"{son.id} looked under the table, then near the chair, trying to make the small mystery make sense.")
    world.para()

    # Act 3
    solve_mystery(world, son, item, mystery, parent, sibling)
    world.para()
    if mystery.bad_ending:
        world.say(f"By dinner time, the missing thing was still gone, and {son.id} had to sit with that answer.")
        world.say(f"His hands were empty, and the room was quiet, even though everybody had been together all day.")
    else:
        world.say(f"By the end, {son.id} knew where the missing thing had gone, and the sharing still mattered.")
        world.say(f"He put the item back, but the day had already changed a little.")

    world.facts.update(
        son=son,
        parent=parent,
        sibling=sibling,
        item=item,
        mystery=mystery,
        place=place,
        item_cfg=item_cfg,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    son = f["son"]
    item_cfg = f["item_cfg"]
    mystery = f["mystery"]
    return [
        f'Write a slice-of-life story about a son named {son.id} who shares {item_cfg.label} and then notices a small mystery.',
        f"Tell a gentle story where {son.id} tries to share {item_cfg.phrase} but someone has to explain what happened to the missing thing.",
        f'Write a short child-facing story that includes sharing, a clue, and the mystery of the missing {mystery.missing_label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    son: Entity = f["son"]
    parent: Entity = f["parent"]
    sibling: Entity = f["sibling"]
    item_cfg: ShareThing = f["item_cfg"]
    mystery: Mystery = f["mystery"]
    place: Place = f["place"]

    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {son.id}, a {son.traits[0]} son, and the small day he spent at {place.name}.",
        ),
        QAItem(
            question=f"What did {son.id} want to do with the {item_cfg.label}?",
            answer=f"{son.id} wanted to share the {item_cfg.label} with {sibling.id}. That is why the story started feeling warm and ordinary.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was what happened to the missing {mystery.missing_label}. {son.id} had to follow a clue and learn the answer.",
        ),
        QAItem(
            question=f"Why did the ending feel sad?",
            answer=f"The ending felt sad because the missing {mystery.missing_label} was not coming back, so {son.id} had to finish the day without it.",
        ),
    ]
    if mystery.id == "missing_cookie":
        qa.append(QAItem(
            question=f"What clue helped solve the missing-cookie mystery?",
            answer=f"A little crumb trail on the table helped {son.id} follow the clue to {sibling.id}.",
        ))
    elif mystery.id == "missing_marble":
        qa.append(QAItem(
            question=f"What clue helped solve the missing-marble mystery?",
            answer=f"A blue glint under the couch gave away where the marble had rolled.",
        ))
    else:
        qa.append(QAItem(
            question=f"What clue helped solve the crayon mystery?",
            answer=f"Red and green smudges on the paper showed that the crayons had been used there.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_cfg: ShareThing = f["item_cfg"]
    mystery: Mystery = f["mystery"]
    out = [
        QAItem(question="What does it mean to share something?", answer="To share means to let someone else use or enjoy part of it too."),
        QAItem(question="What is a mystery?", answer="A mystery is something that is not explained yet, so people have to look for clues."),
    ]
    if item_cfg.id == "cookies":
        out.append(QAItem(question="Why do people like cookies?", answer="Cookies are sweet and tasty, so many people like to eat them as a treat."))
    if item_cfg.id == "crayons":
        out.append(QAItem(question="What are crayons for?", answer="Crayons are used for coloring pictures and drawing on paper."))
    if item_cfg.id == "marble":
        out.append(QAItem(question="What is a marble?", answer="A marble is a small round glass toy that can roll under furniture very easily."))
    if mystery.bad_ending:
        out.append(QAItem(question="What is a bittersweet ending?", answer="A bittersweet ending is one that feels partly okay and partly sad at the same time."))
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place exists and the item fits the selected mystery.
valid_story(P, I, M) :- place(P), item(I), mystery(M), compatible(P, I, M).

% The bad ending flag is part of the world model: some mysteries stay sad.
bad_ending(M) :- mystery(M), bad(M).

% Sharing is a core plot instrument.
has_sharing(I) :- item(I), shareable(I).

compatible(P, I, M) :- place(P), item(I), mystery(M), shareable(I).

#show valid_story/3.
#show bad_ending/1.
#show has_sharing/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for iid, it in SHARE_THINGS.items():
        lines.append(asp.fact("item", iid))
        if it.can_be_shared:
            lines.append(asp.fact("shareable", iid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.bad_ending:
            lines.append(asp.fact("bad", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((p, i, m) for (p, i, m) in valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a son, a shared thing, and a small mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=SHARE_THINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"], default="boy")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.mystery is None or c[2] == args.mystery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, mystery = rng.choice(sorted(combos))
    it = SHARE_THINGS[item]
    if args.gender == "boy":
        name = args.name or rng.choice(BOY_NAMES)
    else:
        name = args.name or rng.choice(GIRL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item,
        mystery=mystery,
        name=name,
        gender=args.gender,
        parent=args.parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(PLACES[params.place], SHARE_THINGS[params.item], MYSTERIES[params.mystery], params.name, params.gender, params.parent, params.trait)
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
        print("--- world trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} valid story combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p, i, m in sorted(valid_combos()):
            params = StoryParams(place=p, item=i, mystery=m, name="Noah", gender="boy", parent="mother", trait="curious")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
