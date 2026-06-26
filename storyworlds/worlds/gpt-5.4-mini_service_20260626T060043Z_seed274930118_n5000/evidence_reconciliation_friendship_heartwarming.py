#!/usr/bin/env python3
"""
storyworlds/worlds/evidence_reconciliation_friendship_heartwarming.py
======================================================================

A small heartwarming storyworld about friendship, mistaken blame, and the
gentle power of evidence.

Seed tale shape:
---
Two friends are preparing something special together. One small thing goes
missing, and a misunderstanding makes both friends sad. Then they follow the
clues, discover what really happened, and make up with each other.

World idea:
---
A child-friendly evidence trail turns a worried guess into a kind apology.
The important state changes are emotional:
- worry rises when an item disappears
- hurt rises when blame is spoken too soon
- trust grows when evidence is found and shared honestly
- reconciliation clears the hurt once the truth is understood

The physical state is simple:
- items can be misplaced
- evidence can be collected from locations and objects
- each clue points toward the true cause

This script is intentionally small and constraint-checked so every generated
story has a beginning, a turn, and a warm ending image.
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
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "child", "thing", "pet"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    warm_detail: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    owner: str
    location: str
    important: bool = True


@dataclass
class StoryParams:
    place: str
    lost_item: str
    child_a: str
    child_b: str
    child_a_type: str
    child_b_type: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        warm_detail="sunlight rested on the leaves, and the garden smelled like earth and mint.",
        clues=["muddy_paw", "wind_tug", "sparkle"],
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        warm_detail="the classroom had bright drawings, small tables, and a soft window glow.",
        clues=["crayon_mark", "paper_trail", "button"],
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        warm_detail="the porch was quiet and cozy, with a little mat and a row of flower pots.",
        clues=["footprint", "ribbon", "leaf"],
    ),
}

LOST_ITEMS = {
    "pin": Item(
        id="pin",
        label="star pin",
        phrase="a shiny star pin",
        owner="child_a",
        location="not_found",
    ),
    "book": Item(
        id="book",
        label="picture book",
        phrase="a favorite picture book",
        owner="child_a",
        location="not_found",
    ),
    "jar": Item(
        id="jar",
        label="cookie jar",
        phrase="a little cookie jar",
        owner="child_b",
        location="not_found",
    ),
    "flower": Item(
        id="flower",
        label="paper flower",
        phrase="a paper flower craft",
        owner="child_a",
        location="not_found",
    ),
}

CHILDREN = {
    "aya": ("Aya", "girl"),
    "ben": ("Ben", "boy"),
    "mina": ("Mina", "girl"),
    "noah": ("Noah", "boy"),
    "leah": ("Leah", "girl"),
    "eli": ("Eli", "boy"),
}

TRAITS = ["gentle", "curious", "kind", "careful", "bright", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for item in LOST_ITEMS:
            combos.append((place, item))
    return combos


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def plausible_story(place: str, lost_item: str) -> bool:
    return place in PLACES and lost_item in LOST_ITEMS


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place=place)

    a_name, b_name = params.child_a, params.child_b
    a_type, b_type = params.child_a_type, params.child_b_type

    child_a = world.add_entity(
        Entity(
            id=a_name,
            kind="child",
            type=a_type,
            label=a_name,
            meters={"worry": 0.0, "hurt": 0.0, "trust": 1.0, "joy": 1.0},
            memes={"friendship": 1.0},
        )
    )
    child_b = world.add_entity(
        Entity(
            id=b_name,
            kind="child",
            type=b_type,
            label=b_name,
            meters={"worry": 0.0, "hurt": 0.0, "trust": 1.0, "joy": 1.0},
            memes={"friendship": 1.0},
        )
    )

    item_template = LOST_ITEMS[params.lost_item]
    lost = world.add_item(
        Item(
            id=item_template.id,
            label=item_template.label,
            phrase=item_template.phrase,
            owner=child_a.id,
            location=place.id,
        )
    )

    world.facts.update(
        place=place,
        child_a=child_a,
        child_b=child_b,
        item=lost,
        lost_item=params.lost_item,
        clue_sequence=list(place.clues),
    )
    return world


def introduce(world: World) -> None:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    item = world.facts["item"]
    world.say(
        f"{a.id} and {b.id} were best friends, and they were making something special together."
    )
    world.say(
        f"{a.id} loved {item.phrase}, and {b.id} loved helping with little surprises."
    )


def lose_item(world: World) -> None:
    a = world.facts["child_a"]
    item = world.facts["item"]
    a.meters["worry"] += 1
    world.say(
        f"One day, {a.id} looked for {item.phrase}, but it was gone."
    )
    world.say(world.place.warm_detail)


def suspect_and_hurt(world: World) -> None:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    item = world.facts["item"]
    a.meters["hurt"] += 1
    b.meters["hurt"] += 1
    b.meters["worry"] += 1
    world.say(
        f"{a.id} stared at {b.id} and guessed, too quickly, that {b.id} had moved it."
    )
    world.say(
        f"{b.id} looked sad, because a hasty guess can sting even when it is not fair."
    )


def gather_clue(world: World, clue: str) -> str:
    if clue in world.fired:
        return ""
    world.fired.add((clue,))
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    item = world.facts["item"]

    if clue == "muddy_paw":
        world.say(
            f"Near a flower pot, they found a muddy paw print that did not belong to either friend."
        )
        return "paw print from a pet"
    if clue == "wind_tug":
        world.say(
            f"They noticed a ribbon tucked under a chair, as if a breeze had tugged it there."
        )
        return "a breeze moved the item"
    if clue == "sparkle":
        world.say(
            f"Then {a.id} spotted a tiny sparkle under the bench, just like the missing star pin."
        )
        item.location = "under_bench"
        return "the item was hidden nearby"
    if clue == "crayon_mark":
        world.say(
            f"In the classroom, a tiny crayon mark on a sleeve showed where the book had brushed past."
        )
        item.location = "shelf_corner"
        return "a brush of motion"
    if clue == "paper_trail":
        world.say(
            f"A line of paper scraps led neatly toward the art table, where careful hands had been working."
        )
        item.location = "art_table"
        return "a paper trail"
    if clue == "button":
        world.say(
            f"They found a loose button by the sink, and {b.id} remembered helping a teacher sort crafts there."
        )
        return "help from someone kind"
    if clue == "footprint":
        world.say(
            f"On the porch mat, there was a small footprint, but it pointed toward the door, not away from it."
        )
        return "someone left by the door"
    if clue == "ribbon":
        world.say(
            f"A ribbon caught on a hook showed that the missing thing had simply slipped while being carried."
        )
        return "something slipped"
    if clue == "leaf":
        world.say(
            f"A leaf on the step proved that the wind had visited and nudged the item gently along."
        )
        return "the wind helped move it"
    return ""


def reconcile(world: World) -> None:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    item = world.facts["item"]

    a.meters["hurt"] = max(0.0, a.meters["hurt"] - 1.0)
    b.meters["hurt"] = max(0.0, b.meters["hurt"] - 1.0)
    a.meters["trust"] += 1.0
    b.meters["trust"] += 1.0
    a.memes["friendship"] += 1.0
    b.memes["friendship"] += 1.0
    world.say(
        f"When the clues fit together, {a.id} took a breath and said sorry for guessing too fast."
    )
    world.say(
        f"{b.id} smiled softly, forgave {a.id}, and together they found {item.phrase} again."
    )
    world.say(
        f"At the end, the two friends sat close together, happy that the truth had brought them back to each other."
    )


def tell_story(world: World) -> World:
    introduce(world)
    world.para()
    lose_item(world)
    suspect_and_hurt(world)

    world.para()
    clue_order = list(world.place.clues)
    random.Random(0).shuffle(clue_order)
    discovered = []
    for clue in clue_order:
        discovered.append(gather_clue(world, clue))
        if world.facts["item"].location != "not_found":
            break

    world.para()
    reconcile(world)
    world.facts["discovered"] = discovered
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place and lost item exist.
valid_story(Place, Item) :- place(Place), lost_item(Item).

% Evidence is enough when at least one clue points to the item being nearby,
% a breeze moving it, or a kind helper having carried it.
has_evidence(Place, Item) :- clue(Place, nearby_item(Item)).
has_evidence(Place, Item) :- clue(Place, moved_by_wind(Item)).
has_evidence(Place, Item) :- clue(Place, carried_by_friend(Item)).

% Reconciliation is reasonable when evidence exists.
reconciles(Place, Item) :- valid_story(Place, Item), has_evidence(Place, Item).

#show valid_story/2.
#show has_evidence/2.
#show reconciles/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            if clue in {"muddy_paw", "footprint"}:
                lines.append(asp.fact("clue", pid, f"nearby_item({LOST_ITEMS['pin'].id})"))
            elif clue in {"wind_tug", "leaf"}:
                lines.append(asp.fact("clue", pid, f"moved_by_wind({LOST_ITEMS['pin'].id})"))
            else:
                lines.append(asp.fact("clue", pid, f"carried_by_friend({LOST_ITEMS['pin'].id})"))
    for item_id in LOST_ITEMS:
        lines.append(asp.fact("lost_item", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program(""))
    asp_valid = set(asp.atoms(model, "valid_story"))
    py_valid = set((p, i) for p, i in valid_combos())
    if asp_valid == py_valid:
        print(f"OK: ASP matches Python gate ({len(py_valid)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_valid - py_valid))
    print("only in Python:", sorted(py_valid - asp_valid))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    item = f["item"]
    place = world.place.label
    return [
        f'Write a heartwarming story about two friends in {place} who lose {item.phrase} and find it through evidence.',
        f"Tell a gentle story where {a.id} and {b.id} misunderstand each other, then reconcile when the clues make the truth clear.",
        f"Write a child-friendly story that includes evidence, friendship, and a happy apology in {place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["child_a"]
    b = world.facts["child_b"]
    item = world.facts["item"]
    place = world.place.label
    return [
        QAItem(
            question=f"Why did {a.id} feel upset in {place}?",
            answer=f"{a.id} felt upset because {item.phrase} was missing, and {a.id} worried it had been lost.",
        ),
        QAItem(
            question=f"How did the friends fix their misunderstanding?",
            answer=f"They looked closely at the evidence, learned what really happened, and then said sorry to each other.",
        ),
        QAItem(
            question=f"What changed between {a.id} and {b.id} by the end?",
            answer=f"They were friends again, and their trust grew after the truth came out kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is evidence?",
            answer="Evidence is a clue or fact that helps show what really happened.",
        ),
        QAItem(
            question="Why is it good to listen before blaming a friend?",
            answer="It is good to listen first because a friend can feel hurt if you blame them before you know the truth.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make up after a disagreement and become friendly again.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and treating them kindly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for iid, it in world.items.items():
        lines.append(f"{iid}: location={it.location} owner={it.owner}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_names() -> list[tuple[str, str]]:
    keys = list(CHILDREN.keys())
    combos = []
    for a in keys:
        for b in keys:
            if a != b:
                combos.append((a, b))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.lost_item and args.lost_item not in LOST_ITEMS:
        raise StoryError("Unknown lost item.")
    if args.place and args.lost_item and not plausible_story(args.place, args.lost_item):
        raise StoryError("That place and item do not make a plausible story together.")

    place = args.place or rng.choice(list(PLACES))
    lost_item = args.lost_item or rng.choice(list(LOST_ITEMS))
    a_key, b_key = rng.choice(valid_names())
    a_name, a_type = CHILDREN[a_key]
    b_name, b_type = CHILDREN[b_key]
    return StoryParams(
        place=place,
        lost_item=lost_item,
        child_a=a_name,
        child_b=b_name,
        child_a_type=a_type,
        child_b_type=b_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world = tell_story(world)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="garden", lost_item="pin", child_a="Aya", child_b="Ben", child_a_type="girl", child_b_type="boy"),
    StoryParams(place="classroom", lost_item="book", child_a="Mina", child_b="Noah", child_a_type="girl", child_b_type="boy"),
    StoryParams(place="porch", lost_item="flower", child_a="Leah", child_b="Eli", child_a_type="girl", child_b_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about evidence, friendship, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost-item", dest="lost_item", choices=LOST_ITEMS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show reconciles/2."))
        atoms = sorted(set(asp.atoms(model, "reconciles")))
        print(f"{len(atoms)} reconcile-able stories:\n")
        for place, item in atoms:
            print(f"  {place:10} {item}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.lost_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
